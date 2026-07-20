import React, { useEffect, useState } from 'react';
import { libraryApi, Book, LibraryMember, BookIssue } from '../../api/library';
import { toast } from 'sonner';

type Tab = 'books' | 'members' | 'issues' | 'overdue';

export default function LibraryPage() {
  const [tab, setTab] = useState<Tab>('books');
  const [books, setBooks] = useState<Book[]>([]);
  const [members, setMembers] = useState<LibraryMember[]>([]);
  const [issues, setIssues] = useState<BookIssue[]>([]);
  const [overdue, setOverdue] = useState<BookIssue[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editBook, setEditBook] = useState<Book | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [issueForm, setIssueForm] = useState<{ bookId: string; memberId: string; dueDate: string } | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      if (tab === 'books') setBooks(await libraryApi.listBooks());
      else if (tab === 'members') setMembers(await libraryApi.listMembers());
      else if (tab === 'issues') setIssues(await libraryApi.listIssues({ is_returned: false }));
      else setOverdue(await libraryApi.listOverdue());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // Always load overdue count for the badge
    libraryApi.listOverdue().then(setOverdue).catch(() => {});
  }, [tab]);

  const submitBook = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editBook) {
        await libraryApi.updateBook(editBook.id, {
          title: form.title, author: form.author, isbn: form.isbn,
          total_copies: Number(form.total_copies || 1), price: Number(form.price || 0),
        });
        toast.success('Book updated');
      } else {
        await libraryApi.createBook({
          title: form.title, author: form.author, isbn: form.isbn,
          total_copies: Number(form.total_copies || 1), price: Number(form.price || 0),
        });
        toast.success('Book added');
      }
      setShowForm(false); setEditBook(null); setForm({});
      load();
    } catch { toast.error('Failed to save book'); }
  };

  const openEditBook = (b: Book) => {
    setEditBook(b);
    setForm({ title: b.title, author: b.author, isbn: b.isbn ?? '', total_copies: String(b.total_copies), price: String(b.price ?? 0) });
    setShowForm(true);
  };

  const submitIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!issueForm) return;
    await libraryApi.issueBook({
      book_id: issueForm.bookId,
      member_id: issueForm.memberId,
      due_date: issueForm.dueDate,
    });
    setIssueForm(null);
    load();
  };

  const handleReturn = async (issueId: string) => {
    if (!confirm('Mark this book as returned?')) return;
    await libraryApi.returnBook(issueId);
    load();
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Library Management</h1>
        {(tab === 'books' || tab === 'members') && (
          <button onClick={() => { setEditBook(null); setShowForm(true); setForm({}); }}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            + Add {tab === 'books' ? 'Book' : 'Member'}
          </button>
        )}
        {tab === 'issues' && (
          <button onClick={() => setIssueForm({ bookId: '', memberId: '', dueDate: '' })}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            + Issue Book
          </button>
        )}
      </div>

      {overdue.length > 0 && tab !== 'overdue' && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700 cursor-pointer"
          onClick={() => setTab('overdue')}>
          ⚠ {overdue.length} book(s) are overdue. Click to view.
        </div>
      )}

      <div className="flex space-x-1 mb-6 border-b">
        {[{ key: 'books', label: 'Books' }, { key: 'members', label: 'Members' },
          { key: 'issues', label: 'Active Issues' }, { key: 'overdue', label: `Overdue (${overdue.length})` }]
          .map(t => (
            <button key={t.key} onClick={() => setTab(t.key as Tab)}
              className={`px-4 py-2 text-sm font-medium rounded-t ${tab === t.key ? 'bg-white border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>
              {t.label}
            </button>
          ))}
      </div>

      {loading ? (
        <div className="text-center py-10 text-gray-500">Loading...</div>
      ) : (
        <>
          {tab === 'books' && (
            <table className="w-full text-sm border rounded overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  {['Accession No.', 'Title', 'Author', 'ISBN', 'Total', 'Available', 'Status', 'Actions'].map(h => (
                    <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {books.map(b => (
                  <tr key={b.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-xs">{b.accession_number}</td>
                    <td className="px-4 py-2 font-medium">{b.title}</td>
                    <td className="px-4 py-2 text-gray-600">{b.author || '—'}</td>
                    <td className="px-4 py-2 text-gray-500 text-xs">{b.isbn || '—'}</td>
                    <td className="px-4 py-2">{b.total_copies}</td>
                    <td className="px-4 py-2">
                      <span className={b.available_copies === 0 ? 'text-red-600 font-semibold' : 'text-green-700'}>
                        {b.available_copies}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${b.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {b.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <button onClick={() => openEditBook(b)} className="text-xs text-indigo-600 hover:underline mr-2">Edit</button>
                      <button onClick={() => setIssueForm({ bookId: b.id, memberId: '', dueDate: '' })} className="text-xs text-green-600 hover:underline" disabled={b.available_copies === 0}>Issue</button>
                    </td>
                  </tr>
                ))}
                {books.length === 0 && (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No books found.</td></tr>
                )}
              </tbody>
            </table>
          )}

          {tab === 'members' && (
            <table className="w-full text-sm border rounded overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  {['Member ID', 'Type', 'Max Books', 'Status'].map(h => (
                    <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {members.map(m => (
                  <tr key={m.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono font-medium">{m.member_id}</td>
                    <td className="px-4 py-2 capitalize">{m.member_type}</td>
                    <td className="px-4 py-2">{m.max_books_allowed}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${m.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {m.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
                {members.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">No members found.</td></tr>
                )}
              </tbody>
            </table>
          )}

          {(tab === 'issues' || tab === 'overdue') && (
            <table className="w-full text-sm border rounded overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  {['Issue Date', 'Due Date', 'Return Date', 'Fine', 'Action'].map(h => (
                    <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(tab === 'issues' ? issues : overdue).map(issue => (
                  <tr key={issue.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2">{issue.issue_date}</td>
                    <td className="px-4 py-2">
                      <span className={new Date(issue.due_date) < new Date() && !issue.is_returned ? 'text-red-600 font-semibold' : ''}>
                        {issue.due_date}
                      </span>
                    </td>
                    <td className="px-4 py-2">{issue.return_date || <span className="text-gray-400">Pending</span>}</td>
                    <td className="px-4 py-2">
                      {issue.fine_amount > 0
                        ? <span className="text-red-600">₹{(issue.fine_amount / 100).toFixed(2)}</span>
                        : '—'}
                    </td>
                    <td className="px-4 py-2">
                      {!issue.is_returned && (
                        <button onClick={() => handleReturn(issue.id)}
                          className="text-green-600 hover:underline text-xs">Return</button>
                      )}
                    </td>
                  </tr>
                ))}
                {(tab === 'issues' ? issues : overdue).length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No records found.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </>
      )}

      {showForm && tab === 'books' && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Add Book</h2>
            <form onSubmit={submitBook} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                <input required value={form.title || ''} onChange={e => setForm({ ...form, title: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Author</label>
                  <input value={form.author || ''} onChange={e => setForm({ ...form, author: e.target.value })}
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ISBN</label>
                  <input value={form.isbn || ''} onChange={e => setForm({ ...form, isbn: e.target.value })}
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Total Copies</label>
                  <input type="number" min="1" value={form.total_copies || '1'}
                    onChange={e => setForm({ ...form, total_copies: e.target.value })}
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price (paise)</label>
                  <input type="number" value={form.price || ''}
                    onChange={e => setForm({ ...form, price: e.target.value })}
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border rounded hover:bg-gray-50">Cancel</button>
                <button type="submit" className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                  Add Book
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {issueForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm">
            <h2 className="text-lg font-semibold mb-4">Issue Book</h2>
            <form onSubmit={submitIssue} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Book *</label>
                <select required value={issueForm.bookId}
                  onChange={e => setIssueForm({ ...issueForm, bookId: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm">
                  <option value="">-- Select --</option>
                  {books.filter(b => b.available_copies > 0).map(b => (
                    <option key={b.id} value={b.id}>{b.title} ({b.available_copies} avail.)</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Member *</label>
                <select required value={issueForm.memberId}
                  onChange={e => setIssueForm({ ...issueForm, memberId: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm">
                  <option value="">-- Select --</option>
                  {members.filter(m => m.is_active).map(m => (
                    <option key={m.id} value={m.id}>{m.member_id} ({m.member_type})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date *</label>
                <input required type="date" value={issueForm.dueDate}
                  onChange={e => setIssueForm({ ...issueForm, dueDate: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setIssueForm(null)}
                  className="px-4 py-2 text-sm border rounded hover:bg-gray-50">Cancel</button>
                <button type="submit" className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                  Issue
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
