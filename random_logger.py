from datetime import datetime
import random
import time

word_list = [
    "apple", "banana", "cherry", "date", "elderberry",
    "fig", "grape", "honeydew", "kiwi", "lemon",
    "mango", "nectarine", "orange", "papaya", "quince",
    "raspberry", "strawberry", "tangerine", "ugli", "vanilla",
    "watermelon", "xigua", "yuzu", "zucchini"
]

while True:
    now = datetime.now()
    random_word = random.choice(word_list)
    readable_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Hola amigo! the time {readable_time} is now...")
    print(f"Take a break, have a {random_word} :)")
    time.sleep(3)