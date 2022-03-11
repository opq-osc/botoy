do
	if opq.sdk then
		return
	end
end

local sdk = {}

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
---@param receiver fun(data:GroupMsgData)
function _G.register_group(receiver)
	if not _G.receive_group_msg then
		function _G.receive_group_msg(ctx)
			for _, r in ipairs(state.group_receivers) do
				if r(ctx) == true then
					return
				end
			end
		end
	end
	table.insert(state.group_receivers, receiver)
end

---注册一个好友消息接收器
---@param receiver fun(data:FriendMsgData)
function _G.register_friend(receiver)
	if not _G.receive_friend_msg then
		function _G.receive_friend_msg(ctx)
			for _, r in ipairs(state.friend_receivers) do
				if r(ctx) == true then
					return
				end
			end
		end
	end
	table.insert(state.friend_receivers, receiver)
end

---注册一个事件接收器
---@param receiver fun(data:EventData)
function _G.register_event(receiver)
	if not _G.receive_events then
		function _G.receive_events(ctx)
			for _, r in ipairs(state.event_receivers) do
				if r(ctx) == true then
					return
				end
			end
		end
	end
	table.insert(state.event_receivers, receiver)
end

return sdk
