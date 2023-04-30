from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from nltk import Tree
from itertools import permutations

# Constants
PARAPHRASES_LIMIT = 20


# Create your views here.

class TreeSerializer(serializers.Serializer):
    tree = serializers.CharField()


def generate_paraphrases(tree):
    tree = Tree.fromstring(tree)
    paraphrases = []
    for subtree in tree.subtrees(lambda t: t.label() == 'NP' and len(t) > 1):
        if all([i.label() == 'NP' or i.label() == 'CC' or i.label() == ',' for i in subtree]):
            for pos in tree.treepositions():
                if tree[pos] == subtree:
                    index = pos
            indexes_to_permute = [subtree.index(i) for i in subtree if i.label() == 'NP']
            permutations_list = list(permutations(indexes_to_permute))
            for permutation in permutations_list:
                permuted_list = subtree.copy()
                for i in range(len(permutation)):
                    permuted_list[indexes_to_permute[i]] = subtree[permutation[i]]
                new_tree = tree.copy(deep=True)
                new_tree[index] = permuted_list
                paraphrases.append({'tree': str(new_tree)})
    return paraphrases


class ParaphraseView(APIView):
    serializer_class = TreeSerializer

    def get(self, request):
        tree = request.query_params.get('tree', None)
        limit = request.query_params.get('limit', PARAPHRASES_LIMIT)

        if tree is None:
            return Response({'error': 'Missing tree parameter'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            paraphrases = generate_paraphrases(tree)

        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TreeSerializer(data=paraphrases[0:int(limit)], many=True)
        if serializer.is_valid():
            return Response({'paraphrases': serializer.data})
        else:
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
