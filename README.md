# NexaFlow Sample Asset MVP

Streamlit proof-of-value for NexaFlow Asset Tracking & Operational Visibility.

## Run

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Working demo workflows

- Sample Intake
- Check Out
- Return Sample
- Move Location
- Report Damage
- Automatic current-state updates
- Automatic lifecycle timeline events
- Executive activity feed

All records currently persist only for the active Streamlit session. NeonDB and Supabase Storage are intentionally deferred until the operational workflow is validated.
