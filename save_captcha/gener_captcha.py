from captcha.image import ImageCaptcha
from captcha.audio import AudioCaptcha
import random
import string
import os

current_path = str(os.getcwd())  # C2: os.path.dirname(os.path.realpath(__file__))


def gener_ImageCaptcha():
    # Create an image instance of the gicen size
    image = ImageCaptcha(width=280, height=90)

    # Image captcha text
    captcha_text = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    # generate the image of the given text
    image.generate(captcha_text)

    # write the image on the given file and save it
    image.write(captcha_text, current_path + '/image_captcha/' + str(captcha_text) + '.png')


def gener_AudioCaptcha():
    # Create an audio instance
    audio = AudioCaptcha()

    # Audio captcha text
    captcha_text = ''.join(random.choices(string.digits, k=10))

    # generate the audio of the given text
    audio.generate(captcha_text)

    # Give the name of the audio file
    audio_file = current_path + '/audio_captcha/' + captcha_text + '.wav'

    # Finally write the audio file and save it
    audio.write(captcha_text, audio_file)


if __name__ == '__main__':
    # print(os.listdir(current_path))
    gener_ImageCaptcha()
    gener_AudioCaptcha()
