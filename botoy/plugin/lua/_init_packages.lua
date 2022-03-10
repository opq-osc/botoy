local opq = _G.opq

require("opq.utils")

local submodules = { json = true, inspect = true, log = true }

setmetatable(opq, {
	__index = function(t, k)
		if submodules[k] then
			t[k] = require("opq." .. k)
			return t[k]
		end
	end,
})
