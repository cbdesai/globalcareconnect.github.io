async function loadInclude(path, selector) {
    try {
        const res = await fetch(path);
        if (!res.ok) return;
        const html = await res.text();
        document.querySelectorAll(selector).forEach(el => el.innerHTML = html);
    } catch (e) {
        console.error('include load failed', path, e);
    }
}

async function loadAllIncludes() {
    const inPages = location.pathname.includes('/pages/');
    const prefix = inPages ? '../' : '';

    await loadInclude(prefix + 'includes/header.html', '[data-include="header"]');
    await loadInclude(prefix + 'includes/footer.html', '[data-include="footer"]');

    // Adjust nav links so they work from root and from pages/ directory
    document.querySelectorAll('[data-include] a[data-href]').forEach(a => {
        const target = a.getAttribute('data-href');
        if (!target) return;
        // If we're already inside pages/, convert 'pages/foo.html' -> 'foo.html'
        const pagePath = inPages ? target.replace(/^pages\//, '') : target;
        a.href = pagePath;
    });

    // Adjust logo link
    document.querySelectorAll('[data-include] a[data-home]').forEach(a => {
        a.href = inPages ? '../index.html' : 'index.html';
    });
}

document.addEventListener('DOMContentLoaded', loadAllIncludes);
