_G.opq = opq
_G.import = import
_G._to_lua_value = _to_lua_value
_G._unpacks_lua_table = _unpacks_lua_table

local opq = _G.opq

require 'opq.utils'

local submodules = { json = true, inspect = true, log = true, parser = true }

setmetatable(opq, {
  __index = function(t, k)
    if submodules[k] then
      t[k] = require('opq.' .. k)
      return t[k]
    end
  end,
})

opq.sdk = require 'opq.sdk'
