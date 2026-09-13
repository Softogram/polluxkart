import { renderHook, act } from '@testing-library/react';
import { useDebouncedState } from '../src/hooks/useDebounce';

// Mock timers
jest.useFakeTimers();

describe('useDebouncedState Hook', () => {
  afterEach(() => {
    jest.clearAllTimers();
  });

  test('returns initial values', () => {
    const { result } = renderHook(() => useDebouncedState('', 500));
    const [value, setValue, debouncedValue] = result.current;
    
    expect(value).toBe('');
    expect(debouncedValue).toBe('');
    expect(typeof setValue).toBe('function');
  });

  test('updates immediate value instantly but debounces the debounced value', () => {
    const { result } = renderHook(() => useDebouncedState('', 500));

    // Update value
    act(() => {
      result.current[1]('hello');
    });

    // Immediate value should update right away
    expect(result.current[0]).toBe('hello');
    // Debounced value should still be empty
    expect(result.current[2]).toBe('');

    // Fast forward time
    act(() => {
      jest.advanceTimersByTime(500);
    });

    // Now debounced value should be updated
    expect(result.current[2]).toBe('hello');
  });

  test('cancels previous timer on rapid updates', () => {
    const { result } = renderHook(() => useDebouncedState('', 500));

    // Rapid updates
    act(() => {
      result.current[1]('a');
    });
    act(() => {
      jest.advanceTimersByTime(200);
    });
    
    act(() => {
      result.current[1]('ab');
    });
    act(() => {
      jest.advanceTimersByTime(200);
    });
    
    act(() => {
      result.current[1]('abc');
    });

    // Immediate value should be 'abc'
    expect(result.current[0]).toBe('abc');
    // Debounced value should still be empty (timers keep getting reset)
    expect(result.current[2]).toBe('');

    // Wait for full delay
    act(() => {
      jest.advanceTimersByTime(500);
    });

    // Both should now be 'abc'
    expect(result.current[0]).toBe('abc');
    expect(result.current[2]).toBe('abc');
  });

  test('works with custom delay', () => {
    const { result } = renderHook(() => useDebouncedState('', 1000));

    act(() => {
      result.current[1]('test');
    });

    // At 500ms, debounced value should still be empty
    act(() => {
      jest.advanceTimersByTime(500);
    });
    expect(result.current[2]).toBe('');

    // At 1000ms, debounced value should be updated
    act(() => {
      jest.advanceTimersByTime(500);
    });
    expect(result.current[2]).toBe('test');
  });
});
