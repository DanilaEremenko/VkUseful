import vk_api
import json
from collections import Counter


def auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция.
    """

    # Код двухфакторной аутентификации
    key = input("Enter authentication code: ")
    # Если: True - сохранить, False - не сохранять.
    remember_device = True

    return key, remember_device


def get_api(login, password, token=None):
    """ Пример обработки двухфакторной аутентификации """
    vk_session = vk_api.VkApi(
        login, password,
        # функция для обработки двухфакторной аутентификации
        auth_handler=auth_handler,
        token=token
    )

    if token is None:
        try:
            vk_session.auth()
        except vk_api.AuthError as error_msg:
            print(error_msg)

    return vk_session.get_api()


if __name__ == '__main__':
    with open('config.json') as config_fp:
        config_dict = json.load(config_fp)

    api = get_api(
        **config_dict['api']
    )

    # get members
    members_ids = api.groups.getMembers(group_id=config_dict['group_id'])['items']
    members_str = ','.join([str(curr_member_id) for curr_member_id in members_ids])
    members_info = api.users.get(user_ids=members_str)

    # get info about users
    user_list = []
    all_group_names = []
    for i, member in enumerate(members_info):
        try:
            curr_group_ids = api.groups.get(user_id=member['id'])['items']

            str_groups = ','.join([str(curr_group_id) for curr_group_id in curr_group_ids])
            curr_group_names = [curr_group_info['name'] for curr_group_info in api.groups.getById(group_ids=str_groups)]
            all_group_names = [*all_group_names, *curr_group_names]

            user_list.append(
                {
                    'member': {
                        'first_name': member['first_name'],
                        'last_name': member['last_name'],
                        'id': member['id']
                    },
                    'groups': curr_group_names
                }
            )
            print(f"{i}: done")
        except Exception as e:
            print(f"{i}: bitch has private profile")

    # calculate popularity of follower groups
    most_popular_groups = Counter(all_group_names).most_common()
    for group in most_popular_groups:
        if group[1] > config_dict['threshold'] and group[0] not in config_dict['exception_groups']:
            print("%d:%s" % (group[1], group[0]))

    # get users with bad group
    bad_user_list = []
    for user in user_list:
        if config_dict['bad_group_name'] in user['groups']:
            bad_user_list.append(user)
