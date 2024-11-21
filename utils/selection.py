def calculate_weight(comment, max_likes):
    """
    计算评论的权重，基于点赞数和评分极端性。

    参数:
    - comment: 包含评论数据的对象，包含 likes（点赞数）和 rating（评分）等属性
    - max_likes: 所有评论中最大的点赞数

    返回:
    - 计算出的权重值
    """
    like_score = 0.6 * (comment.likes / max_likes) if max_likes > 0 else 0
    rating_score = 0.4 * abs(comment.rating - 3) / 2  # 评分因子，范围在0到1之间
    return like_score + rating_score

def select_comments(comments, max_count):
    """
    筛选并返回评论的子集，用于 AI 总结。

    参数:
    - comments: 所有评论的列表
    - max_count: 向 AI 提供的最大评论数量

    返回:
    - 筛选出的评论列表
    """
    # 分类评论
    positive = [c for c in comments if c.rating > 3]
    neutral = [c for c in comments if c.rating == 3]
    negative = [c for c in comments if c.rating < 3]

    # 计算正面和负面评论的比例
    total_comments = len(positive) + len(negative)
    if total_comments == 0:
        pos_ratio = 0.5
        neg_ratio = 0.5
    else:
        pos_ratio = len(positive) / total_comments
        neg_ratio = len(negative) / total_comments

    # 动态设定数量配额
    pos_quota = max(int(max_count * pos_ratio), 1)  # 至少保留1条正面评论
    neg_quota = max(int(max_count * neg_ratio), 1)  # 至少保留1条负面评论

    # 计算每个评论的权重
    max_likes = max(c.likes for c in comments) or 1

    # 对每个类别的评论按权重排序
    positive = sorted(positive, key=lambda c: calculate_weight(c, max_likes), reverse=True)
    neutral = sorted(neutral, key=lambda c: calculate_weight(c, max_likes), reverse=True)
    negative = sorted(negative, key=lambda c: calculate_weight(c, max_likes), reverse=True)

    # 选取评论，确保每类评论的最低数量
    selected_positive = positive[:pos_quota]
    selected_negative = negative[:neg_quota]

    # 若负面或正面评论不足，则从其他类别补充
    if len(selected_negative) < neg_quota:
        required_negatives = neg_quota - len(selected_negative)
        additional_comments = sorted(selected_positive[pos_quota:] + neutral, key=lambda c: calculate_weight(c, max_likes))[:required_negatives]
        selected_negative.extend(additional_comments)

    if len(selected_positive) < pos_quota:
        required_positives = pos_quota - len(selected_positive)
        additional_comments = sorted(selected_negative[neg_quota:] + neutral, key=lambda c: calculate_weight(c, max_likes))[:required_positives]
        selected_positive.extend(additional_comments)

    # 合并所有选中的评论
    selected_comments = selected_positive + selected_negative

    # 若总数量超过限制，按权重重新排序并截断
    if len(selected_comments) > max_count:
        selected_comments = sorted(selected_comments, key=lambda c: calculate_weight(c, max_likes), reverse=True)[:max_count]

    return selected_comments
