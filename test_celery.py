from src.nia.nova.core.celery_app import create_thread

result = create_thread.delay("Test Thread", "test")
print(f"Task ID: {result.id}")
print(f"Task result: {result.get()}")
