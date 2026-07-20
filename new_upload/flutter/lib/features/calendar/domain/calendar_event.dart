import '../../../shared/utils/format.dart';

class CalendarEvent {
  const CalendarEvent({
    required this.title,
    this.type,
    this.date,
    this.isHoliday = false,
  });

  final String title;
  final String? type;
  final DateTime? date;
  final bool isHoliday;

  factory CalendarEvent.fromJson(Map<String, dynamic> j,
      {bool isHoliday = false}) {
    return CalendarEvent(
      title: (j['title'] ?? j['name'] ?? j['event_name'] ?? 'Event').toString(),
      type: (j['event_type'] ?? j['type'])?.toString() ??
          (isHoliday ? 'Holiday' : null),
      date: Fmt.parseDate(
          j['start_datetime'] ?? j['date'] ?? j['event_date'] ?? j['start_date']),
      isHoliday: isHoliday,
    );
  }
}
