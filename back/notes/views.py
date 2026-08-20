from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Note
from .serializers import NoteSerializer


class NoteListCreateView(APIView):
    """GET /api/notes/  — list my notes
    POST /api/notes/ — create a note
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        notes = Note.objects.filter(owner=request.user)
        return Response(NoteSerializer(notes, many=True).data)

    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(owner=request.user)
        return Response(
            NoteSerializer(note).data,
            status=status.HTTP_201_CREATED,
        )


class NoteDetailView(APIView):
    """GET/PATCH/DELETE /api/notes/<id>/"""

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
