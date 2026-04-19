import re

with open('app/dashboard/page.tsx', 'r') as f:
    content = f.read()

# 1. Add searchInput state and debounce effect after existing search state
content = content.replace(
    "const [search, setSearch] = useState('');",
    """const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 400);
    return () => clearTimeout(timer);
  }, [searchInput]);"""
)

# 2. Update the input onChange to use searchInput
content = content.replace(
    "onChange={e => { setSearch(e.target.value); setPage(1); }}",
    "onChange={e => { setSearchInput(e.target.value); setPage(1); }}"
)

# 3. Update input value to show searchInput (so user sees what they type)
content = content.replace(
    "value={search}",
    "value={searchInput}"
)

with open('app/dashboard/page.tsx', 'w') as f:
    f.write(content)

print("✅ Done! Search debounce applied.")
