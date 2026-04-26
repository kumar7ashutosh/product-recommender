from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import ChatOpenAI
from src.config import Config
class RAGChainBuilder:
    def __init__(self,vector_store):
        self.vector_store=vector_store
        self.model = ChatOpenAI(model=Config.RAG_MODEL , temperature=0.5)
        self.history_store={}
    def _get_history(self,session_id:str) -> BaseChatMessageHistory:
        if session_id not in self.history_store:
            self.history_store[session_id] = ChatMessageHistory()
        return self.history_store[session_id]
    def build_chain(self):
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        context_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given the chat history and user question, rewrite it as a standalone question."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an e-commerce assistant.

        Rules:
        1. If relevant context is available → use it to answer
        2. If context is irrelevant or empty → answer using general knowledge
        3. Do NOT say "I don't have context"
        4. Always try to help the user
        5. Keep answers concise and practical

        CONTEXT:
        {context}
        """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        # Step 1: Rewrite query using history
        rewrite_chain = context_prompt | self.model

        # Step 2: Retrieve docs
        def retrieve(inputs):
            standalone_q = rewrite_chain.invoke(inputs).content
            docs = retriever.invoke(standalone_q)

            # convert docs → string (IMPORTANT)
            context_text = "\n\n".join([doc.page_content for doc in docs])

            return context_text

        # Step 3: Answer generation
        rag_chain = (
            RunnablePassthrough.assign(context=retrieve)
            | qa_prompt
            | self.model
        )

        return RunnableWithMessageHistory(
            rag_chain,
            self._get_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )