from ai import ask_friend

while True:
    message = input("You: ")

    if message.lower() == "exit":
        break

    try:
        reply = ask_friend(message)
        print("Koro:", reply)
    except Exception as e:
        print("ERROR:", e)