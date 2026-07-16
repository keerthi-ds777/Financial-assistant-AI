from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("data/FIL_Stock Market.pdf")
documents = loader.load()
print(documents)