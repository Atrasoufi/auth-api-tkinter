from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Note
from .serializers import NoteSerializer

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


class NoteListCreateView(APIView):
    """GET /api/notes/?search=&page=&page_size=
    POST /api/notes/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Note.objects.filter(owner=request.user)

        search = (request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(body__icontains=search))

        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (TypeError, ValueError):
            page = 1

        try:
            page_size = int(request.query_params.get("page_size", DEFAULT_PAGE_SIZE))
        except (TypeError, ValueError):
            page_size = DEFAULT_PAGE_SIZE
        page_size = max(1, min(page_size, MAX_PAGE_SIZE))

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        notes = qs[start:end]

        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "total_pages": max(1, (total + page_size - 1) // page_size),
                "results": NoteSerializer(notes, many=True).data,
            }
        )

    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(owner=request.user)
        return Response(
            NoteSerializer(note).data,
            status=status.HTTP_201_CREATED,
        )


class NoteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_note(self, request, pk):
        try:
            return Note.objects.get(pk=pk, owner=request.user)
        except Note.DoesNotExist:
            return None

    def get(self, request, pk):
        note = self._get_note(request, pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(NoteSerializer(note).data)

    def patch(self, request, pk):
        note = self._get_note(request, pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NoteSerializer(note, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        note = self._get_note(request, pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
