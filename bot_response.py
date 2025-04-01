import os
import re
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder,format_document
from typing import List, Tuple
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langchain_core.runnables import Runnable, RunnableBranch, RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
# from prompt_templates import QUESTION_ANSWER_PROMPT, STANDALONE_QUESTION_PROMPT, GENERATE_FOLLOWUP_QUESTIONS_PROMPT #, TEST_QUESTION_ANSWER_PROMPT
from operator import itemgetter
from constants import clear_orphaned_history_messages, remove_oldest_conversation_if_needed, DB_NAME, HISTORY_COLLECTION_NAME
from utils import format_context
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
load_dotenv()
async def generate_answer(question, ensemble_retriever, chat_history,llm_model, prompts):   
    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(prompts['STANDALONE_QUESTION_PROMPT'])
    ANSWER_PROMPT = ChatPromptTemplate.from_messages(
        [
            ("system", prompts['QUESTION_ANSWER_PROMPT']),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{question}"),
        ]
    )

    DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")

    def _combine_documents(docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"):
        formatted_docs = [format_document(doc, document_prompt) for doc in docs]
        return document_separator.join(formatted_docs)

    def _format_chat_history(chat_history: List[Tuple[str, str]]) -> List:
        buffer = []
        for human, ai in chat_history:
            buffer.append(HumanMessage(content=human))
            buffer.append(AIMessage(content=ai))
        return buffer

    class ChatHistory(BaseModel):
        chat_history: List[Tuple[str, str]] = Field(..., description="The chat history as a list of tuples")
        question: str

    _search_query = RunnableBranch(
        (
            RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
                run_name="HasChatHistoryCheck"
            ), 
            RunnablePassthrough.assign(
                chat_history=lambda x: _format_chat_history(x["chat_history"])
            )
            |
            CONDENSE_QUESTION_PROMPT
            | llm_model
            | StrOutputParser(),
        ),
        RunnableLambda(itemgetter("question")),
    )

    _inputs = RunnableParallel(
        {
            "question": lambda x: x["question"],
            "chat_history": lambda x: _format_chat_history(x["chat_history"]),
            "context": _search_query | ensemble_retriever | _combine_documents,
        }
    ).with_types(input_type=ChatHistory)

    chain = _inputs | ANSWER_PROMPT | llm_model | StrOutputParser()

    response = chain.invoke({
                "question": question,
                "chat_history": chat_history
            })
    return response


async def generate_follow_up_questions(chat_history: List[Tuple], current_question: str,ensemble_retreiver,llm_model, prompts) -> any:
    class GenerateQuestionsOutput(BaseModel):
        questions: List[str] = Field(description="List of suggested questions")
    
    try:

        parser = JsonOutputParser(pydantic_object=GenerateQuestionsOutput)
        response_parser = parser.get_format_instructions()
        prompt_template = PromptTemplate(
            template=prompts['GENERATE_FOLLOWUP_QUESTIONS_PROMPT'],
            input_variables=["chat_history", "current_question", "context",],
            partial_variables={"format_instructions":response_parser}

        )
        
        context=ensemble_retreiver.invoke(current_question)
        template_chain: Runnable = prompt_template | llm_model | parser
        formatted_chat_history = ''.join([f'<Question>{question} <Answer>{answer}\n ' for question, answer in chat_history])
        

        response = template_chain.invoke({
            "chat_history": formatted_chat_history,
            "current_question": current_question,
            "context": context
        })
        return response
    except Exception as e:
        print("ERRROR :  ", e)




def remove_think_step(text):
    thinking_pattern=r"\n?<think>.*?</think>\n?"
    clean_text=re.sub(thinking_pattern,"",text,flags=re.DOTALL)
    return clean_text

async def generate_answer_v2(question: str, session_id:str, retriever, llm_model, prompts):
    standalone_question_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompts['STANDALONE_QUESTION_PROMPT']),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    parse_output = StrOutputParser()
    question_chain = standalone_question_prompt | llm_model | parse_output
    retriever_chain = RunnablePassthrough.assign(context=question_chain | retriever | format_context)

    rag_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompts['QUESTION_ANSWER_PROMPT']),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    rag_chain = (
        retriever_chain
        | rag_prompt
        | llm_model
        | parse_output
    )

    def get_session_history(session_id: str) -> MongoDBChatMessageHistory:
        return MongoDBChatMessageHistory(os.getenv("MONGO_DB_URI"), session_id, database_name=DB_NAME, collection_name=HISTORY_COLLECTION_NAME)


    with_message_history = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history",
    )

    # async def main_chatbot(user_input: str, session_id: str) -> dict:
    # await clear_orphaned_history_messages()
    await remove_oldest_conversation_if_needed(session_id)
    response = with_message_history.invoke({"question": question}, {"configurable": {"session_id": session_id}})
    return {'status': 'success', 'answer': response}
    # return await main_chatbot(question, session_id)