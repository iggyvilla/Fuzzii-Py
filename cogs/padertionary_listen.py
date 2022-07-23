from firebase_admin import firestore
from typing import List
from google.cloud.firestore_v1.watch import DocumentChange
from google.cloud.firestore_v1.base_document import DocumentSnapshot
import threading
import interactions

db = firestore.client()

# Create an Event for notifying main thread.
callback_done = threading.Event()


# Create a callback on_snapshot function to capture changes
def on_snapshot(doc_snapshot: List[DocumentSnapshot], changes: List[DocumentChange], read_time):

    for change in changes:
        if change.type.name == 'ADDED':
            pass
        elif change.type.name == 'MODIFIED':
            pass
        elif change.type.name == 'REMOVED':
            pass

    callback_done.set()


doc_ref = db.collection(u'padertionary').on_snapshot(on_snapshot)

while True:
    pass
