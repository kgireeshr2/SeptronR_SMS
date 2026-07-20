import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../../shared/widgets/search_field.dart';
import '../application/library_providers.dart';

class LibraryScreen extends ConsumerWidget {
  const LibraryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Library'),
          bottom: const TabBar(
            indicatorColor: Colors.white,
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            tabs: [Tab(text: 'Catalog'), Tab(text: 'Issued')],
          ),
        ),
        body: const TabBarView(children: [_Catalog(), _MyBooks()]),
      ),
    );
  }
}

class _Catalog extends ConsumerStatefulWidget {
  const _Catalog();

  @override
  ConsumerState<_Catalog> createState() => _CatalogState();
}

class _CatalogState extends ConsumerState<_Catalog> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(bookSearchProvider(_query));
    return Column(
      children: [
        SearchField(
          hint: 'Search books…',
          onChanged: (v) => setState(() => _query = v),
        ),
        Expanded(
          child: async.when(
            loading: () => const LoadingView(),
            error: (e, _) => ErrorView(
              message: e.toString(),
              onRetry: () => ref.invalidate(bookSearchProvider(_query)),
            ),
            data: (books) {
              if (books.isEmpty) {
                return const EmptyView(
                    message: 'No books found', icon: Icons.menu_book_outlined);
              }
              return ListView.separated(
                itemCount: books.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (_, i) {
                  final b = books[i];
                  return ListTile(
                    leading: const Icon(Icons.book_outlined,
                        color: AppColors.primary),
                    title: Text(b.title),
                    subtitle: Text([
                      if (b.author != null) b.author,
                      if (b.categoryName != null) b.categoryName,
                    ].whereType<String>().join(' · ')),
                    trailing: AppBadge(
                      text: b.isAvailable
                          ? 'Available${b.availableCopies != null ? ' (${b.availableCopies})' : ''}'
                          : 'Out of stock',
                      color: b.isAvailable ? AppColors.success : AppColors.danger,
                    ),
                  );
                },
              );
            },
          ),
        ),
      ],
    );
  }
}

class _MyBooks extends ConsumerWidget {
  const _MyBooks();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(bookIssuesProvider);
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(bookIssuesProvider),
      ),
      data: (issues) {
        if (issues.isEmpty) {
          return const EmptyView(message: 'No issued books');
        }
        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(bookIssuesProvider),
          child: ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: issues.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, i) {
              final it = issues[i];
              return Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.gray200),
                ),
                child: ListTile(
                  title: Text(it.bookTitle ?? 'Book',
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: Text([
                    if (it.issueDate != null) 'Issued ${Fmt.date(it.issueDate)}',
                    if (it.dueDate != null) 'due ${Fmt.date(it.dueDate)}',
                  ].join(' · ')),
                  trailing: AppBadge(
                    text: it.returnDate != null
                        ? 'Returned'
                        : it.isOverdue
                            ? 'Overdue'
                            : 'Issued',
                    color: it.returnDate != null
                        ? AppColors.success
                        : it.isOverdue
                            ? AppColors.danger
                            : AppColors.warning,
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }
}
