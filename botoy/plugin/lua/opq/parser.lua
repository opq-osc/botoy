local py_parsers = {
	group = import("botoy.parser.group"),
	friend = import("botoy.parser.friend"),
	event = import("botoy.parser.friend"),
}

local function gen_parsers(name)
	local py_parser = py_parsers[name]
	return setmetatable({}, {
		__index = function(t, k)
			---@param ctx userdata|table
			local func = function(ctx)
				if type(ctx) == "table" then -- 直接传接收函数参数，就自动取ctx，方便
					ctx = ctx.ctx
				end
				local data = py_parser[k](ctx)
				return data and _to_lua_table(data.dict()) or data
			end

			t[k] = func
			return func
		end,
	})
end

return {
	group = gen_parsers("group"),
	friend = gen_parsers("friend"),
	event = gen_parsers("event"),
}
