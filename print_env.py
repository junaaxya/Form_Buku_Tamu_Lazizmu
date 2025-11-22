from dotenv import load_dotenv; load_dotenv()
import os
print('DATABASE_URL =', os.getenv('DATABASE_URL'))
