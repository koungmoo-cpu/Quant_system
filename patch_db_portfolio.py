from backend.services.db_connector import DBConnector

db = DBConnector()
portfolio = db.get_virtual_portfolio()
for item in portfolio:
    if 'Error: GOOGLE_GENAI_API_KEY' in item.get('setup', ''):
        ticker = item.get('Ticker', item.get('ticker'))
        if ticker:
            doc_ref = db.db.collection('virtual_portfolio').document(ticker)
            doc_ref.set({'setup': '[AI_Fallback] '}, merge=True)
            print(f"Patched portfolio item: {ticker}")
