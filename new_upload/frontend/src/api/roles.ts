import api from './axios';

export interface PermissionResponse {
  id: string;
  module: string;
  action: string;
  description?: string;
}

export interface RoleResponse {
  id: string;
  school_id?: string;
  name: string;
  slug: string;
  description?: string;
  is_system: boolean;
  is_active: boolean;
  permissions: string[]; // ["students:view", ...]
}

export interface RoleCreate {
  name: string;
  slug: string;
  description?: string;
}

export interface RoleUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export const rolesApi = {
  list: () => api.get<RoleResponse[]>('/roles'),
  get: (id: string) => api.get<RoleResponse>(`/roles/${id}`),
  create: (data: RoleCreate) => api.post<RoleResponse>('/roles', data),
  update: (id: string, data: RoleUpdate) => api.put<RoleResponse>(`/roles/${id}`, data),
  delete: (id: string) => api.delete(`/roles/${id}`),
  getPermissions: (id: string) => api.get<PermissionResponse[]>(`/roles/${id}/permissions`),
  assignPermissions: (id: string, permissionIds: string[]) =>
    api.post<PermissionResponse[]>(`/roles/${id}/permissions`, { permission_ids: permissionIds }),
  clone: (id: string, name: string) =>
    api.post<RoleResponse>(`/roles/${id}/clone`, { name }),
  allPermissions: () => api.get<PermissionResponse[]>('/permissions'),
};
