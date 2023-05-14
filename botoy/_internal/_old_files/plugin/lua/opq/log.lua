local logger = import('botoy').logger

local log = {}

local function gen_logger(level, format)
  return function(...)
    local items = {}
    for _, item in ipairs { ... } do
      table.insert(items, tostring(item))
    end

    local msg
    if format then
      msg = string.format(table.remove(items, 1), unpack(items))
    else
      msg = table.concat(items, ' ')
    end

    logger[level](msg)
  end
end

log.debug = gen_logger 'debug'
log.debugF = gen_logger('debug', true)
log.info = gen_logger 'info'
log.infoF = gen_logger('info', true)
log.warn = gen_logger 'warning'
log.warnF = gen_logger('warning', true)
log.error = gen_logger 'error'
log.errorF = gen_logger('error', true)

return log
