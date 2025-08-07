document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const hasQuery = Array.from(urlParams.keys()).length > 0;

    const results = document.getElementById('results');
    const noResults = document.getElementById('no-results');

    if (hasQuery) {
        if (results) {
            results.scrollIntoView({ behavior: 'smooth' });
        } else if (noResults) {
            noResults.scrollIntoView({ behavior: 'smooth' });
        }
    }
});
