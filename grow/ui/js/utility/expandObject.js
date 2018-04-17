/**
 * Expand a short keyed object ('key.subkey') into a full object.
 */

export default function expandObject(original) {
  const expanded = {}

  for (const prop in original) {
    deepExpandPath(expanded, prop, original[prop])
  }

  return expanded
}

function deepExpandPath(obj, path, value) {
  const parts = path.split('.')
  if (parts.length == 1) {
    if (Array.isArray(value)) {
      deepExpandArray(value)
    }
    obj[path] = value
  } else {
    const initialKey = parts[0]
    if (initialKey in obj === false) {
      obj[initialKey] = {}
      deepExpandPath(obj[initialKey], parts.slice(1).join('.'), value)
    }
  }
}

function deepExpandArray(arr) {
  for (let i = 0; i < arr.length; i++) {
    if (typeof arr[i] === 'object') {
      arr[i] = expandObject(arr[i])
    } else if (Array.isArray(arr[i])) {
      deepExpandArray(arr[i])
    } else {
      console.warn('Unknown deep expand for array: ', arr[i])
    }
  }
}
