import { writable } from 'svelte/store';

export const faceDbStats = writable<{ total_people: number; total_encodings: number }>({
	total_people: 0,
	total_encodings: 0
});
export const faceMatchResults = writable<any[]>([]);
