import time
import random
import logging

famous_quotes = [
    "The only limit to our realization of tomorrow is our doubts of today - Franklin D Roosevelt",
    "In the middle of every difficulty lies opportunity - Albert Einstein",
    "Life is what happens when you're busy making other plans - John Lennon",
    "Do not go where the path may lead go instead where there is no path and leave a trail - Ralph Waldo Emerson",
    "Success is not final failure is not fatal It is the courage to continue that counts - Winston Churchill",
    "You miss 100 of the shots you dont take - Wayne Gretzky",
    "It is not our abilities that show what we truly are it is our choices - Dumbledore",
    "It always seems impossible until its done - Nelson Mandela",
    "Do what you can with what you have where you are - Theodore Roosevelt",
    "Our lives begin to end the day we become silent about things that matter - Martin Luther King Jr",
    "I think therefore I am - Rene Descartes",
    "The journey of a thousand miles begins with one step - Lao Tzu",
    "That which does not kill us makes us stronger - Friedrich Nietzsche",
    "Happiness is not something ready made It comes from your own actions - Dalai Lama",
    "In three words I can sum up everything Ive learned about life It goes on - Robert Frost",
    "Believe you can and you're halfway there - Theodore Roosevelt",
    "The unexamined life is not worth living - Socrates",
    "Be the change you wish to see in the world - Mahatma Gandhi",
    "Dont count the days make the days count - Muhammad Ali",
    "Strive not to be a success but rather to be of value - Albert Einstein",
    "Its not whether you get knocked down its whether you get up - Vince Lombardi",
    "If opportunity doesnt knock build a door - Milton Berle",
    "The only thing we have to fear is fear itself - Franklin D Roosevelt",
    "To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment - Ralph Waldo Emerson",
    "I have not failed Ive just found 10000 ways that wont work - Thomas Edison",
    "You must be the change you wish to see in the world - Mahatma Gandhi",
    "To infinity and beyond - Buzz Lightyear",
    "Dont cry because its over smile because it happened - Dr Seuss",
    "You only live once but if you do it right once is enough - Mae West",
    "Dream big and dare to fail - Norman Vaughan",
    "Everything youve ever wanted is on the other side of fear - George Addair",
    "If life were predictable it would cease to be life and be without flavor - Eleanor Roosevelt",
    "The best way to predict the future is to create it - Peter Drucker",
    "The mind is everything What you think you become - Buddha",
    "In the end we only regret the chances we didnt take - Lewis Carroll",
    "What we think we become - Buddha",
    "I have learned over the years that when ones mind is made up this diminishes fear - Rosa Parks",
    "Success is how high you bounce when you hit bottom - George S Patton",
    "Everything has beauty but not everyone sees it - Confucius",
    "You must expect great things of yourself before you can do them - Michael Jordan",
    "It does not matter how slowly you go as long as you do not stop - Confucius",
    "Do or do not There is no try - Yoda",
    "Act as if what you do makes a difference It does - William James",
    "Whether you think you can or think you cant youre right - Henry Ford",
    "Life isnt about getting and having its about giving and being - Kevin Kruse",
    "We must not allow other peoples limited perceptions to define us - Virginia Satir",
    "Too many of us are not living our dreams because we are living our fears - Les Brown",
    "Twenty years from now you will be more disappointed by the things that you didnt do than by the ones you did do - Mark Twain"
]

logger = logging.getLogger("RandomQuoteLogger")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
log_format = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
formatter = logging.Formatter(log_format)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

while True:
    logger.debug(random.choice(famous_quotes))
    time.sleep(3)
    logger.info(random.choice(famous_quotes))
    time.sleep(3)
    logger.warning(random.choice(famous_quotes))
    time.sleep(3)
    logger.error(random.choice(famous_quotes))
    time.sleep(3)
    logger.critical(random.choice(famous_quotes))
    time.sleep(3)