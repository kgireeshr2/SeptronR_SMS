import api from './api';
import { TimetableSlot } from '@/types';

export const timetableService = {
  getByClass: (class_id: string, section_id: string) =>
    api.get<TimetableSlot[]>('/timetable', { params: { class_id, section_id } }).then((r) => r.data),

  getMyTimetable: () =>
    api.get<TimetableSlot[]>('/timetable/my').then((r) => r.data),
};
