#!/bin/bash
set -e

echo "Waiting for database services to become healthy..."
# We can use netcat or wait-for-it, but here we can just sleep a bit or check python connections
python -c "
import time, sqlalchemy
for db in ['mysql+mysqlconnector://wms_user:wmspassword@mysql_source:3306/inventory_wms', 'postgresql+psycopg2://dw_admin:dwpassword@postgres_dwh:5432/inventory_dw']:
    connected = False
    for i in range(15):
        try:
            engine = sqlalchemy.create_engine(db)
            with engine.connect() as conn:
                pass
            print(f'Successfully connected to {db}')
            connected = True
            break
        except Exception as e:
            print(f'Waiting for {db} ({i+1}/15)... {str(e)}')
            time.sleep(2)
    if not connected:
        raise Exception(f'Could not connect to {db}')
"

echo "Databases are ready!"

# Option to populate mock data if the database is empty
if [ "$POPULATE_MOCK_DATA" = "true" ]; then
    echo "Running mock data generator..."
    python src/mock_generator.py
fi

echo "Running ETL pipeline..."
python src/pipeline.py
