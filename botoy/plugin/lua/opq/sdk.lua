do
	if opq.sdk then
		return
	end
end

local sdk = {}
local botoy = import("botoy")

local state = {
	group_receivers = {},
	friend_receivers = {},
	event_receivers = {},
}

---设置插件基本信息
---@param help string: 帮助信息
---@param name string: 插件名称
function _G.set_info(help, name)
	_G.__name__ = name
	_G.__doc__ = help
end

---@class GroupMsgData
---@field bot number: 机器人qq
---@field data table: 消息数据
---@field ctx userdata: 消息对象

---@class FriendMsgData
---@field bot number: 机器人qq
---@field data table: 消息数据
---@field ctx userdata: 消息对象

---@class EventData
---@field bot number: 机器人qq
---@field data table: 消息数据
---@field ctx userdata: 消息对象

---注册一个群消息接收器
---@vararg fun(data:GroupMsgData)
function _G.register_group(...)
	if not _G.receive_group_msg then
		function _G.receive_group_msg(ctx)
			for _, r in ipairs(state.group_receivers) do
				if r(ctx) == true then
					return
				end
			end
		end
	end
	for _, receiver in ipairs({ ... }) do
		table.insert(state.group_receivers, receiver)
	end
end

---注册一个好友消息接收器
---@vararg fun(data:FriendMsgData)
function _G.register_friend(...)
	if not _G.receive_friend_msg then
		function _G.receive_friend_msg(ctx)
			for _, r in ipairs(state.friend_receivers) do
				if r(ctx) == true then
					return
				end
			end
		end
	end
	for _, receiver in ipairs({ ... }) do
		table.insert(state.friend_receivers, receiver)
	end
end

---注册一个事件接收器
---@vararg fun(data:EventData)
function _G.register_event(...)
	if not _G.receive_events then
		function _G.receive_events(ctx)
			for _, r in ipairs(state.event_receivers) do
				if r(ctx) == true then
					return
				end
			end
		end
	end
	for _, receiver in ipairs({ ... }) do
		table.insert(state.event_receivers, receiver)
	end
end

---@class S
---@field text function
---@field image function
---@field voice function

---获取发送语法糖
---@param ctx table|userdata
---@return S
function sdk.create_s(ctx)
	if type(ctx) == "table" then
		ctx = ctx.ctx
	end
	assert(type(ctx) == "userdata") -- 简单的验证

	return {
		_S_ref = botoy.S.bind(ctx),
		---发送文字
		---@param self any
		---@param text string: 发送的文字
		---@param at boolean: 是否艾特发送该消息的用户， 默认为 false
		---@return table|nil
		text = function(self, text, at)
			if at == nil then
				at = false
			end
			return _to_lua_value(self._S_ref.text(text, at))
		end,
		---发送图片
		---@param self any
		---@param data string|string[]: 发送的数据，链接，路径，md5， MD5列表, base64
		---@param text string: 发送文字默认为空
		---@param at boolean: 是否艾特发送该消息的用户, 默认为false
		---@return table|nil
		image = function(self, data, text, at)
			if at == nil then
				at = false
			end
			return _to_lua_value(self._S_ref.image(data, text or "", at, 0)) -- S的数据类型判断足够稳定
		end,
		---发送语音
		---@param data string|string[]: 发送的数据，链接，路径，base64
		---@return table|nil
		voice = function(self, data)
			return _to_lua_value(self._S_ref.voice(data, 0))
		end,
	}
end

---新建Action
---@param qq nil|number: bot qq号
---@param port nil|number
---@param host nil|string
---@param timeout nil|number
---@return table
function sdk.create_action(qq, port, host, timeout, ctx)
	return setmetatable({
		_action = ctx and botoy.Action.from_ctx(ctx) or botoy.Action(qq, port, host, timeout or 20),
	}, {
		__index = function(t, k) -- 可能需要单独导出属性
			---@param args table
			local func = function(args)
				return _to_lua_value(_unpacks_lua_table(t._action[k])(args))
			end
			t[k] = func
			return func
		end,
	})
end

---从ctx创建Action
---@param ctx any
---@return table
function sdk.create_action_from_ctx(ctx)
	if type(ctx) == "table" then
		ctx = ctx.ctx
	end
	return sdk.create_action(nil, nil, nil, nil, ctx)
end

return sdk
