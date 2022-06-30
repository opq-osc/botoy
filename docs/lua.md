# Lua 插件

全局变量/函数, 后面有括号表示函数，其他表示模块:

- opq

  - opq.startswith()
  - opq.endswith()
  - opq.inspect()

  - opq.json

    - opq.json.encode()
    - opq.json.decode()

  - opq.log

    - opq.log.debug()
    - opq.log.debugF()
    - opq.log.info()
    - opq.log.infoF()
    - opq.log.warn()
    - opq.log.warnF()
    - opq.log.error()
    - opq.log.errorF()

  - opq.parser(botoy.parser)

    - opq.parser.group
    - opq.parser.friend
    - opq.parser.event

  - opq.sdk

    - opq.sdk.create_s()
    - opq.sdk.create_action()
    - opq.sdk.create_action_from_ctx()

- import()
- set_info()
- register_group()
- register_friend()
- register_event()
