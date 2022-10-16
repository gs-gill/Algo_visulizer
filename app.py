import asyncio
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async

MAX_MESSAGES_CNT = 10 ** 4

chat_msgs = []  # (name, msg)
online_users = set()  #


async def refresh_msg(my_name, msg_box, user_box):
    """send new message to current session"""
    global chat_msgs
    last_idx = len(chat_msgs)
    while True:
        await asyncio.sleep(0.5)
        for m in chat_msgs[last_idx:]:
            if m[0] != my_name:  # only refresh message that not sent by current user
                msg_box.append(put_markdown('`%s`: %s' % m, sanitize=True))
                user_box.reset()
                for u in online_users:
                    user_box.append(u)

        # remove expired message
        if len(chat_msgs) > MAX_MESSAGES_CNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)


async def main():
    global chat_msgs

    put_markdown("Welcome to the chat room, you can chat with all the people currently online.")

    msg_box = output()
    user_box = output()
    with use_scope('first'):
        put_row([put_scrollable(msg_box, height=300, keep_bottom=True), None, put_scrollable(user_box, height=300)])
    nickname = await input("Your nickname", required=True,
                           validate=lambda
                               n: 'This name is already been used' if n in online_users or n == '📢' else None)

    online_users.add(nickname)
    user_box.append(*online_users)
    chat_msgs.append(('📢', '`%s` joins the room. %s users currently online' % (nickname, len(online_users))))
    msg_box.append(put_markdown('`📢`: `%s` join the room. %s users currently online' % (nickname, len(online_users)),
                                sanitize=True))

    @defer_call
    def on_close():
        online_users.remove(nickname)
        chat_msgs.append(('📢', '`%s` leaves the room. %s users currently online' % (nickname, len(online_users))))

    refresh_task = run_async(refresh_msg(nickname, msg_box, user_box))

    while True:
        data = await input_group('Send message', [
            input(name='msg'),
            actions(name='cmd', buttons=['Send', {'label': 'Exit', 'type': 'cancel'}])
        ], validate=lambda d: ('msg', 'Message content cannot be empty') if d['cmd'] == 'Send' and not d[
            'msg'] else None)
        if data is None:
            break
        msg_box.append(put_markdown('`%s`: %s' % (nickname, data['msg']), sanitize=True))
        chat_msgs.append((nickname, data['msg']))

    refresh_task.close()
    toast("You have left the chat room")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8080)
    args = parser.parse_args()
    start_server(main, port=args.port, websocket_ping_interval=30, debug=True)
