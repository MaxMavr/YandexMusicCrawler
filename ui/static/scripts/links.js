export function getArtistUrl(artist_id) {
    if (!artist_id) {
        console.warn('getArtistUrl: передан некорректный объект исполнителя');
        return '#';
    }
    return `https://music.yandex.ru/artist/${artist_id}`;
}

export function getArtistAvatar(artist_cover_uri, resolution = 50) {
    if (!artist_cover_uri) return '';
    const size = Number(resolution);
    if (isNaN(size) || size <= 0) {
        console.warn('Некорректный размер, используем 50');
        return 'https://' + artist_cover_uri.replace('/1000x1000', '/50x50');
    }
    return 'https://' + artist_cover_uri.replace('/1000x1000', `/${size}x${size}`);
}