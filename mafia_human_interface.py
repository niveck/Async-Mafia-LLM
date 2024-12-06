# TODO: change file name to player_merged_chat_and_input.py after committing (so git will remember the history of the file)
from threading import Thread
from termcolor import colored
from player_chat import read_game_text_loop, welcome_player, game_over_message
from player_input import write_text_to_game_loop

THREADING_WARNING_MESSAGE = "Pay attention! This interface allows you to read and write in the " \
                            "same terminal, but it is not recommended!\n" \
                            "It is better to use different terminals for viewing the chat and " \
                            "for entering input:" \
                            "\t`player_chat.py` and `player_input.py`, respectively."
WARNING_COLOR = "light_red"


def game_read_and_write_loop(name, is_mafia):
    write_thread = Thread(target=write_text_to_game_loop, args=(name, is_mafia))
    # daemon: writing in the background, so it can stop when eliminated and still allow reading
    write_thread.daemon = True
    write_thread.start()
    read_game_text_loop(is_mafia)


def main():
    print(colored(THREADING_WARNING_MESSAGE, WARNING_COLOR))
    name, is_mafia = welcome_player()
    game_read_and_write_loop(name, is_mafia)
    game_over_message()


if __name__ == '__main__':
    main()
