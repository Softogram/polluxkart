import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for debouncing a value
 * @param {any} value - The value to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {any} - The debounced value
 */
export function useDebounce(value, delay = 500) {
  // Initialize with empty string to prevent immediate filtering on first character
  const [debouncedValue, setDebouncedValue] = useState('');
  const isFirstRender = useRef(true);

  useEffect(() => {
    // On first render, don't set the value immediately if it's empty
    if (isFirstRender.current) {
      isFirstRender.current = false;
      // Only set initial value if it's not empty (e.g., from URL params)
      if (value) {
        setDebouncedValue(value);
      }
      return;
    }

    // For subsequent changes, always debounce
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Custom hook for debounced state - returns both the immediate value and setter,
 * plus the debounced value
 * @param {any} initialValue - Initial value
 * @param {number} delay - Delay in milliseconds
 * @returns {[any, Function, any]} - [immediateValue, setValue, debouncedValue]
 */
export function useDebouncedState(initialValue = '', delay = 500) {
  const [value, setValue] = useState(initialValue);
  const [debouncedValue, setDebouncedValue] = useState(initialValue);
  const timerRef = useRef(null);

  const setValueWithDebounce = useCallback((newValue) => {
    setValue(newValue);
    
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    
    timerRef.current = setTimeout(() => {
      setDebouncedValue(newValue);
    }, delay);
  }, [delay]);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return [value, setValueWithDebounce, debouncedValue];
}

/**
 * Custom hook for debounced callback
 * @param {Function} callback - The callback to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} - The debounced callback
 */
export function useDebouncedCallback(callback, delay = 500) {
  const timeoutRef = useRef(null);

  const debouncedCallback = useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
}

export default useDebounce;
