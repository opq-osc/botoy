local opq = _G.opq

---Tests if `s` starts with `prefix`.
---
---@param s string: a string
---@param prefix string: a prefix
---@return boolean: true if `prefix` is a prefix of s
function opq.startswith(s, prefix)
  return s:sub(1, #prefix) == prefix
end

--- Tests if `s` ends with `suffix`.
---
---@param s string: a string
---@param suffix string: a suffix
---@return boolean: true if `suffix` is a suffix of s
function opq.endswith(s, suffix)
  return #suffix == 0 or s:sub(-#suffix) == suffix
end
