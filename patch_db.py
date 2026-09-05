from backend.services.db_connector import DBConnector

db = DBConnector()
setups = db.get_latest_detected_setups()
if setups and 'items' in setups:
    for item in setups['items']:
        if 'Error: GOOGLE_GENAI_API_KEY' in item.get('ai_summary', ''):
            item['ai_summary'] = '[AI_Fallback] ' + item.get('ai_summary', '').replace('Error: GOOGLE_GENAI_API_KEY is not set. Cannot perform AI analysis.', '')
    
    db.save_detected_setups(setups)
    print("Patched latest_setups in DB.")
