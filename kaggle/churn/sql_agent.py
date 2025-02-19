from langchain.chains import LLMChain
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from pyhive import hive
from langchain.prompts import PromptTemplate

# Connect LangChain to Ollama running Mistral
llm = Ollama(model="mistral", base_url="http://localhost:3000")

# Spark Thrift Server connection (use PyHive for Hive)
conn = hive.Connection(host='localhost', port=4040, username='your_username')

# Initialize LangChain SQL Database
db = SQLDatabase(conn)

# Define a prompt template for SQL querying
prompt = PromptTemplate(
    input_variables=["question"],
    template="Given the following SQL database, answer the question: {question}"
)

# Create LLMChain with the prompt template and the Ollama model
llm_chain = LLMChain(prompt=prompt, llm=llm)

# Example Query
question = "What are the top 5 products with the highest sales?"
response = llm_chain.run({"question": question})

print(response)
