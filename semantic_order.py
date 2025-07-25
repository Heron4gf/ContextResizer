import chromadb
import uuid

def order_messages(context, query):
    # use chromadb to create a collection and retrieve the most similar messages to the query ordered by distance
    # the collection shouldn't be saved on disk so that we can use it only for this function

    # Create an ephemeral client with an in-memory database
    client = chromadb.EphemeralClient()
    
    # Create a collection with a unique name to avoid conflicts
    collection_name = f"messages_{uuid.uuid4().hex}"
    collection = client.create_collection(collection_name)
    
    # Add all context messages to the collection
    # Assuming context is a list of strings
    if context:
        ids = [str(i) for i in range(len(context))]
        collection.add(documents=context, ids=ids)
    
    # Query the collection with the provided query
    # Get all documents ordered by similarity
    results = collection.query(
        query_texts=[query],
        n_results=len(context) if context else 0
    )
    
    # Return messages ordered by similarity (distance)
    # The results contain the documents in order of similarity
    if results and 'documents' in results and results['documents']:
        return results['documents'][0]
    else:
        return []
