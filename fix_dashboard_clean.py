dashboard = open('app/dashboard/page.tsx', 'r').read()

# Fix 1: fetchData should take no arguments
old = "stats.depthBreakdown.map(({ suppliers, count, pct }: { suppliers: number, count: number, pct: number })"
new = "stats.depthBreakdown.map(({ suppliers, count, pct }: { suppliers: number; count: number; pct: number })"
dashboard = dashboard.replace(old, new)

# Fix 2: Search button should not pass args to fetchData
old = "onClick={() => { setPage(1); fetchData(searchInput, filterType, 1); }}"
new = "onClick={() => { setSearch(searchInput); setPage(1); }}"
dashboard = dashboard.replace(old, new)

# Fix 3: Filter buttons should not pass args to fetchData
old = "onClick={() => { setFilterType(f); setPage(1); fetchData(search, f, 1); }}"
new = "onClick={() => { setFilterType(f); setPage(1); }}"
dashboard = dashboard.replace(old, new)

# Fix 4: Pagination should not pass args to fetchData
old = "onClick={() => { const p = Math.max(1, page - 1); setPage(p); fetchData(search, filterType, p); }}"
new = "onClick={() => setPage(p => Math.max(1, p - 1))}"
dashboard = dashboard.replace(old, new)

old = "onClick={() => { const p = Math.min(totalPages, page + 1); setPage(p); fetchData(search, filterType, p); }}"
new = "onClick={() => setPage(p => Math.min(totalPages, p + 1))}"
dashboard = dashboard.replace(old, new)

# Fix 5: fetchData back to simple version
old = """  const fetchData = async (searchVal = search, filterVal = filterType, pageVal = page) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ search: searchVal, filter: filterVal, page: String(pageVal) });
      const res = await fetch(`/api/sheet?${params}`);
      const json = await res.json();
      setRows(json.data || []);
      setTotalRows(json.total || 0);
      setTotalPages(json.totalPages || 1);
      if (json.stats) setStats(json.stats);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };"""
new = """  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/sheet');
      const json = await res.json();
      setRows(json.data || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };"""
dashboard = dashboard.replace(old, new)

open('app/dashboard/page.tsx', 'w').write(dashboard)
print("✅ Done!")
