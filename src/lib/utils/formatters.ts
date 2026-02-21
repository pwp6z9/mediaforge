export function formatFileSize(bytes: number): string {
	if (bytes === 0) return '0 B';
	const k = 1024;
	const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));
	return Math.round((bytes / Math.pow(k, i)) * 10) / 10 + ' ' + sizes[i];
}

export function formatDuration(seconds: number): string {
	const h = Math.floor(seconds / 3600);
	const m = Math.floor((seconds % 3600) / 60);
	const s = Math.floor(seconds % 60);
	
	if (h > 0) {
		return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
	}
	return `${m}:${String(s).padStart(2, '0')}`;
}

export function formatDate(isoStr: string): string {
	try {
		const date = new Date(isoStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
	} catch {
		return 'Unknown';
	}
}

export function truncate(str: string, max: number): string {
	if (str.length <= max) return str;
	return str.substring(0, max - 3) + '...';
}

export function getFileIcon(fileType: string): string {
	const type = fileType.toLowerCase();
	if (type.startsWith('audio/') || ['mp3', 'flac', 'wav', 'm4a', 'aac'].some(t => type.includes(t))) {
		return '🎵';
	}
	if (type.startsWith('video/') || ['mp4', 'mkv', 'mov', 'avi', 'webm'].some(t => type.includes(t))) {
		return '🎬';
	}
	if (type.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'webp'].some(t => type.includes(t))) {
		return '🖼️';
	}
	return '📄';
}
