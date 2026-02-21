import { writable } from 'svelte/store';

export const sentryActive = writable<boolean>(false);
export const sentryStatus = writable<Record<string, any>>({});
export const activityLog = writable<any[]>([]);
export const undoQueue = writable<any[]>([]);
