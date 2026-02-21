import { writable } from 'svelte/store';

export const selectedFiles = writable<string[]>([]);
export const currentMetadata = writable<Record<string, any>>({});
export const searchResults = writable<any[]>([]);
export const searchQuery = writable<string>('');
export const searchFilters = writable<Record<string, any>>({});
export const totalResults = writable<number>(0);
export const isIndexing = writable<boolean>(false);
export const indexProgress = writable<{
	total: number;
	processed: number;
	current_file: string;
}>({
	total: 0,
	processed: 0,
	current_file: ''
});
export const dbStats = writable<Record<string, any>>({});
