import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { staffApi, Staff, StaffStatistics } from '../../api/staff';

const unwrap = (res: any) => res?.data ?? res;

const StaffPage: React.FC = () => {
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [statistics, setStatistics] = useState<StaffStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [designationFilter, setDesignationFilter] = useState('');
  const [employmentTypeFilter, setEmploymentTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('active');

  useEffect(() => {
    fetchStaffList();
    fetchStatistics();
  }, [search, departmentFilter, designationFilter, employmentTypeFilter, statusFilter]);

  const fetchStaffList = async () => {
    try {
      setLoading(true);
      const response = await staffApi.listStaff({
        search: search || undefined,
        department_id: departmentFilter || undefined,
        designation_id: designationFilter || undefined,
        employment_type: employmentTypeFilter || undefined,
        is_active: statusFilter === 'all' ? undefined : statusFilter === 'active',
        limit: 100,
      });
      setStaffList(unwrap(response) ?? []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch staff list');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await staffApi.getStaffStatistics();
      setStatistics(unwrap(response));
    } catch (err) {
      console.error('Failed to fetch statistics', err);
    }
  };

  const handleDelete = async (staffId: string) => {
    if (!confirm('Are you sure you want to delete this staff member?')) return;

    try {
      await staffApi.deleteStaff(staffId);
      fetchStaffList();
      fetchStatistics();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete staff member');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Staff Management</h1>
        <div className="flex gap-2">
          <Link
            to="/admin/staff/departments"
            className="border border-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-50 text-sm"
          >
            Departments &amp; Designations
          </Link>
          <Link
            to="/admin/staff/new"
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm"
          >
            Add New Staff
          </Link>
        </div>
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded shadow">
            <h3 className="text-gray-500 text-sm">Total Staff</h3>
            <p className="text-2xl font-bold">{statistics.total_staff}</p>
          </div>
          <div className="bg-green-50 p-4 rounded shadow">
            <h3 className="text-gray-500 text-sm">Active Staff</h3>
            <p className="text-2xl font-bold text-green-600">{statistics.active_staff}</p>
          </div>
          <div className="bg-red-50 p-4 rounded shadow">
            <h3 className="text-gray-500 text-sm">Inactive Staff</h3>
            <p className="text-2xl font-bold text-red-600">{statistics.inactive_staff}</p>
          </div>
          <div className="bg-blue-50 p-4 rounded shadow">
            <h3 className="text-gray-500 text-sm">Departments</h3>
            <p className="text-2xl font-bold text-blue-600">
              {Object.keys(statistics.by_department).length}
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded shadow mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Search by name or employee ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border rounded px-3 py-2"
          />
          <select
            value={employmentTypeFilter}
            onChange={(e) => setEmploymentTypeFilter(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="">All Employment Types</option>
            <option value="permanent">Permanent</option>
            <option value="contract">Contract</option>
            <option value="part_time">Part Time</option>
            <option value="probation">Probation</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Staff List Table */}
      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : error ? (
        <div className="bg-red-50 text-red-600 p-4 rounded">{error}</div>
      ) : (
        <div className="bg-white rounded shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Employee ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Designation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Employment Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {staffList.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    No staff members found
                  </td>
                </tr>
              ) : (
                staffList.map((staff) => (
                  <tr key={staff.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        to={`/admin/staff/${staff.id}`}
                        className="text-blue-600 hover:underline"
                      >
                        {staff.employee_id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">{staff.full_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {staff.department_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {staff.designation_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap capitalize">
                      {staff.employment_type.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          staff.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {staff.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <Link
                        to={`/admin/staff/${staff.id}`}
                        className="text-blue-600 hover:underline mr-3"
                      >
                        View
                      </Link>
                      <Link
                        to={`/admin/staff/${staff.id}/edit`}
                        className="text-green-600 hover:underline mr-3"
                      >
                        Edit
                      </Link>
                      <button
                        onClick={() => handleDelete(staff.id)}
                        className="text-red-600 hover:underline"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default StaffPage;
