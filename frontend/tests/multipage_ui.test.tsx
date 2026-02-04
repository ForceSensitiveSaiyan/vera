import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import HomePage from "../app/page";

const createResponse = (data: unknown) =>
  Promise.resolve(
    new Response(JSON.stringify(data), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  );

const uploadPayload = {
  document_id: "doc-1",
  image_url: "/files/doc-1.png",
  image_width: 0,
  image_height: 0,
  status: "uploaded",
  page_count: 2,
  review_complete: false,
  pages: [
    {
      page_id: "page-1",
      page_index: 0,
      image_url: "/files/page-1.png",
      status: "ocr_done",
      review_complete: false,
    },
    {
      page_id: "page-2",
      page_index: 1,
      image_url: "/files/page-2.png",
      status: "ocr_done",
      review_complete: false,
    },
  ],
  structured_fields: {},
};

const pagePayload = (pageId: string, pageIndex: number) => ({
  document_id: "doc-1",
  page_id: pageId,
  page_index: pageIndex,
  image_url: `/files/${pageId}.png`,
  image_width: 1200,
  image_height: 1600,
  status: "ocr_done",
  review_complete: false,
  tokens: [
    {
      id: `${pageId}-t1`,
      line_id: "line-0",
      line_index: 0,
      token_index: 0,
      text: "Item",
      confidence: 0.2,
      confidence_label: "low",
      forced_review: true,
      bbox: [0, 0, 10, 10],
      flags: [],
    },
    {
      id: `${pageId}-t2`,
      line_id: "line-0",
      line_index: 0,
      token_index: 1,
      text: "Total",
      confidence: 0.4,
      confidence_label: "medium",
      forced_review: false,
      bbox: [12, 0, 10, 10],
      flags: [],
    },
  ],
});

const setupUploadFlow = async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/documents/upload")) {
      return createResponse(uploadPayload);
    }
    if (url.includes("/documents/doc-1/pages/page-1")) {
      return createResponse(pagePayload("page-1", 0));
    }
    if (url.includes("/documents/doc-1/pages/page-2")) {
      return createResponse(pagePayload("page-2", 1));
    }
    return createResponse({});
  });

  vi.stubGlobal("fetch", fetchMock);
  render(<HomePage />);

  const fileInput = document.querySelector("input[type='file']") as HTMLInputElement;
  const file = new File(["dummy"], "sample.pdf", { type: "application/pdf" });
  fireEvent.change(fileInput, { target: { files: [file] } });

  const runButtons = screen.getAllByRole("button", { name: /Run OCR/i });
  const runButton = runButtons.find((button) => !(button as HTMLButtonElement).disabled) ?? runButtons[0];
  fireEvent.click(runButton);

  await screen.findByText(/Page 1 of 2/i);

  return fetchMock;
};

describe("HomePage multipage UI", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows page navigation and moves between pages", async () => {
    await setupUploadFlow();

    const nextButton = screen.getByRole("button", { name: /^Next$/i });
    fireEvent.click(nextButton);

    await screen.findByText(/Page 2 of 2/i);
  });

  it("updates review progress after marking reviewed", async () => {
    await setupUploadFlow();

    await screen.findByText(/2 uncertain items · 0 reviewed · 2 remaining/i);

    const tokenButtons = await screen.findAllByRole("button", { name: /Item/i });
    const tokenButton = tokenButtons.find((button) => button.classList.contains("token-button")) ?? tokenButtons[0];
    fireEvent.click(tokenButton);

    const markReviewed = await screen.findByRole("button", { name: /Mark reviewed/i });
    fireEvent.click(markReviewed);

    await waitFor(() => {
      expect(screen.getByText(/2 uncertain items · 1 reviewed · 1 remaining/i)).toBeInTheDocument();
    });
  });
});
