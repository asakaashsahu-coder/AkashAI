from core.listener import Listener


listener = Listener()

print("Say: Hey Jeroo")

if listener.listen_for_wake_word():

    print("✅ Jeroo activated!")

else:

    print("❌ Wake word not detected.")