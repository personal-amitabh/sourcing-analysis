with open('app/dashboard/page.tsx', 'r') as f:
    content = f.read()

# Replace the search input onChange to not filter live
old = """onChange={e => setSearchInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { setPage(1); fetchData(searchInput, filterType, 1); } }}"""
new = """onChange={e => setSearchInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { setSearch(searchInput); setPage(1); } }}"""
content = content.replace(old, new)

# Fix fetchData to load all rows
old2 = """  const fetchData = async (searchVal = search, filterVal = filterType, pageVal = page) => {
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
new2 = """  const fetchData = async () => {
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
content = content.replace(old2, new2)

with open('app/dashboard/page.tsx', 'w') as f:
    f.write(content)
print("✅ Done!")
